#include "DebloatPass.h"

#include "llvm/Transforms/IPO/GlobalDCE.h"
#include "llvm/Transforms/IPO/StripDeadPrototypes.h"
#include "llvm/IR/DebugInfo.h"

#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/GlobalValue.h"

#include "llvm/Support/raw_ostream.h"

#include <algorithm>

using namespace llvm;

static cl::opt<bool> mydebug("my-debug", cl::desc("Enable errs() print statements"), cl::init(false));
#define DEBUG mydebug

PreservedAnalyses DebloatPass::run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  #ifdef DEBUG
  errs() << "Verbose debug messages enabled.\n";
  #endif

  bool changed = runOnModule(M, MAM);
	return (changed ? llvm::PreservedAnalyses::none()
                  : llvm::PreservedAnalyses::all());

}
bool DebloatPass::runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  initTracedFuncNames();
  removeNonTracedFuncsNgx(M, MAM);
  return false;
}

void DebloatPass::getCallsTo(std::set<llvm::Function *> funcs_to_delete, llvm::Module &M){
  for (Function &F : M){
    for (auto &B : F){
      for (auto &I : B){
        CallBase   *CB = dyn_cast<CallBase>(&I);
            CallInst   *CI = dyn_cast<CallInst>(&I);
            InvokeInst *II = dyn_cast<InvokeInst>(&I);
            if(CB){
              Function *cf = CB->getCalledFunction();
              auto it = funcs_to_delete.find(cf);
              if (it != funcs_to_delete.end()){
                #ifdef DEBUG
                errs() << "Found call to function I need to delete\n";
                errs() << "\t" << cf->getName().str() << "\n";
                #endif
                if (CI){
                  
                }
                else if (II){
                  
                }
              }

            }
      }
    }
  }
}

void deleteFunctionCalls_defuse(Function *F) {
    for (auto UI = F->use_begin(), UE = F->use_end(); UI != UE; ) {
        // Get the use
        Use &U = *UI++;
        CallBase *CB = dyn_cast<CallBase>(U.getUser());
        CallInst *CI = dyn_cast<CallInst>(U.getUser());
        InvokeInst *II = dyn_cast<InvokeInst>(U.getUser());

        // Check if the use is a call or invoke instruction
        if (CB){
          #ifdef DEBUG
          //errs() << "Found CallBase Use: " << *CB << "\n";
          #endif
          if (CI){
            #ifdef DEBUG
            errs() << "Called Function: " << CI->getCalledFunction()->getName().str() << "\n";
            #endif
            // Delete the call instruction
            CI->eraseFromParent();
            #ifdef DEBUG
            errs() << "Erased Call Instruction\n";
            #endif
          }
          else if (II){
            #ifdef DEBUG
            errs() << "Called Function: " << II->getCalledFunction()->getName().str() << "\n";
            errs() << "Erased Invoke Instruction\n";
            #endif
            // Delete the invoke instruction
            II->eraseFromParent();
            #ifdef DEBUG
            errs() << "Erased Invoke Instruction\n";
            #endif
          }
        }
    }
}

bool DebloatPass::removeNonTracedFuncsNgx(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  bool modified = false;

  std::set<llvm::Function *> funcs_to_delete;
  // Iterate over functions in the module
  for (Function &F : M){
	    // Check if the function name is in the traced_func_names vector
      if (std::find(traced_func_names.begin(), traced_func_names.end(), F.getName()) != traced_func_names.end()) {
        // Match found, to remove the function from the module (F.eraseFromParent())
        traced_funcs.insert(&F);
      } else{
        //if (F.getName().contains("llvm")){
          //continue;
        //}
        if (F.getName().contains("ngx")){
          funcs_to_delete.insert(&F);
        }
        
        //F.replaceAllUsesWith(llvm::UndefValue::get(F.getType()));
      }
	}

  #ifdef DEBUG
  // Display deleted function names
  errs() << "Functions of traced_funcs:\n";
  for (auto Func : funcs_to_delete) {
      errs() << Func->getName().str() << "\n";
  }
  errs() << "Num functions to erase: " << funcs_to_delete.size() << "\n";
  #endif

  getCallsTo(funcs_to_delete, M);
  
  int i = 0;
  for (auto *F : funcs_to_delete) {
    #ifdef DEBUG
    if (i%100 == 0){
      errs() << "Erased " << i << " functions.\n";
    }
    #endif
    if (!F){
      #ifdef DEBUG
      errs() << "F is null. Cannot delete\n";
      #endif
      continue;
    }
    if (F->getName().empty()) {
      #ifdef DEBUG
      errs() << "No named function. Cannot delete\n";
      #endif
      continue;
    }
    #ifdef DEBUG
    errs() << "Erasing --" << F->getName().str() << "--\n";
    #endif
    //deleteFunctionCalls(F,M);
    //F->eraseFromParent();
    #ifdef DEBUG
      //errs() << "Erased\n";
    #endif
    i++;
    modified = true;
  }
  GlobalDCEPass().run(M, MAM);
  StripDeadPrototypesPass().run(M, MAM);
  
  return modified;
}

bool DebloatPass::initTracedFuncNames() {
  std::string file_path = "/home/user/passes/py_scripts/nginx_pin.log";

  // Open the file
  std::ifstream file(file_path);

  // Check if the file is opened successfully
  if (!file.is_open()) {
      std::cerr << "Error opening file: " << file_path << std::endl;
      return false;
  }

  // Read the file line by line
  std::string line;
  while (std::getline(file, line)) {
      // Add each line (function name) to the vector
      traced_func_names.push_back(line);
  }

  // Close the file
  file.close();

  #ifdef DEBUG
  /*errs() << "Function Names of traced_func_names:\n";
  for (const auto& name : traced_func_names) {
      errs() << name << "\n";
  }*/
  #endif
  return true;
}


// This is the core interface for pass plugins. It guarantees that 'opt' will
// be able to recognize HelloWorld when added to the pass pipeline on the
// command line, i.e. via '-passes=hello-world'
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "DebloatPass", LLVM_VERSION_STRING,
          [](PassBuilder &PB) {
            PB.registerPipelineParsingCallback(
                [](StringRef Name, ModulePassManager &MPM,
                   ArrayRef<PassBuilder::PipelineElement>) {
                  if (Name == "debloat") {
                    MPM.addPass(DebloatPass());
                    return true;
                  }
                  return false;
                });
          }};
}
