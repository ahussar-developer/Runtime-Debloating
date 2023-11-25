#include "DebloatPass.h"

#include "llvm/Transforms/IPO/GlobalDCE.h"
#include "llvm/Transforms/IPO/StripDeadPrototypes.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/IR/DebugInfo.h"

#include "llvm/Pass.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/GlobalValue.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IR/IRBuilder.h"

#include "llvm/Support/raw_ostream.h"

#include <algorithm>
#include <filesystem>

using namespace llvm;

static cl::opt<bool> mydebug("my-debug", cl::desc("Enable errs() print statements"), cl::init(false));
#define DEBUG mydebug

static cl::opt<bool> printfall("printf-all", cl::desc("Enable printf statements for all functions"), cl::init(false));
#define PRINTFALL printfall

//This cannot be ran at teh same time as printf-all and vice versa
static cl::opt<bool> printfdel("printf-del", cl::desc("Enable printf statements for deleted functions"), cl::init(false));
#define PRINTFDEL printfdel

PreservedAnalyses DebloatPass::run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  #ifdef DEBUG
  errs() << "Verbose debug messages enabled.\n";
  #endif

  bool changed = runOnModule(M, MAM);
	return (changed ? llvm::PreservedAnalyses::none()
                  : llvm::PreservedAnalyses::all());

}

void clearLogs() {
  namespace fs = std::filesystem;
  const char* filename = "/home/user/passes/declaration_functions.log";
  const char* filename2 = "/home/user/passes/kept_functions.log";
  const char* filename3 = "/home/user/passes/deleted_functions.log";

  try {
      fs::remove(filename);
      #ifdef DEBUG
      errs() << "declaration_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef DEBUG
      errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
  try {
      fs::remove(filename2);
      #ifdef DEBUG
      errs() << "kept_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef DEBUG
      errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
  try {
      fs::remove(filename3);
      #ifdef DEBUG
      errs() << "deleted_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef DEBUG
      errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
}
bool DebloatPass::runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  clearLogs();
  initTracedFuncNames();
  initMissedRuntimeFuncNames();
  initStaticModuleFuncNames();
  removeNonTracedFuncs(M, MAM);
  #ifdef DEBUG
  errs() << "Finished removal. Checking module\n";
  #endif
  if (!verifyModule(M, &errs())) {
    errs() << "Module is well-formed.\n";
  } else {
      errs() << "Module has errors!\n";
  }
  #ifdef DEBUG
  logDecFunctions(M);
  #endif
  #ifdef PRINTFALL
  printfAllFuncs(M);
  #endif

  return false;
}

void DebloatPass::printfAllFuncs(llvm::Module &M) {
  auto &CTX = M.getContext();
  PointerType *PrintfArgTy = PointerType::getUnqual(Type::getInt8Ty(CTX));

  // STEP 1: Inject the declaration of printf
  // ----------------------------------------
  // Create (or _get_ in cases where it's already available) the following
  // declaration in the IR module:
  //    declare i32 @printf(i8*, ...)
  // It corresponds to the following C declaration:
  //    int printf(char *, ...)
  FunctionType *PrintfTy = FunctionType::get(
      IntegerType::getInt32Ty(CTX),
      PrintfArgTy,
      /*IsVarArgs=*/true);

  FunctionCallee Printf = M.getOrInsertFunction("printf", PrintfTy);

  // Set attributes as per inferLibFuncAttributes in BuildLibCalls.cpp
  Function *PrintfF = dyn_cast<Function>(Printf.getCallee());
  PrintfF->setDoesNotThrow();
  PrintfF->addParamAttr(0, Attribute::NoCapture);
  PrintfF->addParamAttr(0, Attribute::ReadOnly);


  // STEP 2: Inject a global variable that will hold the printf format string
  // ------------------------------------------------------------------------
  llvm::Constant *PrintfFormatStr = llvm::ConstantDataArray::getString(
      CTX, "%s\n\tArgs=%d\n");

  Constant *PrintfFormatStrVar =
      M.getOrInsertGlobal("PrintfFormatStr", PrintfFormatStr->getType());
  dyn_cast<GlobalVariable>(PrintfFormatStrVar)->setInitializer(PrintfFormatStr);

  // STEP 3: For each function in the module, inject a call to printf
  // ----------------------------------------------------------------
  for (auto &F : M) {
    if (F.isDeclaration())
      continue;

    // Get an IR builder. Sets the insertion point to the top of the function
    IRBuilder<> Builder(&*F.getEntryBlock().getFirstInsertionPt());
    std::string name = F.getName().str();
    std::string final_str;
    auto it = traced_funcs.find(&F);
    auto it2 = missed_runtime_funcs.find(&F);
    auto it3 = static_module_funcs.find(&F);
    if (it != traced_funcs.end()) {
        // F is in traced_funcs
        final_str = name + "-- KEPT";
    } 
    else if (it2 != missed_runtime_funcs.end()) {
      final_str = name + "-- KEPT";
    }
    else if (it3 != static_module_funcs.end()) {
      final_str = name + "-- KEPT";
    }
    else {
        // F is not in traced_funcs
        final_str = name + "-- DELETED";
    }
    // Inject a global variable that contains the function name
    auto print_stmt = Builder.CreateGlobalStringPtr(final_str);

    // Printf requires i8*, but PrintfFormatStrVar is an array: [n x i8]. Add
    // a cast: [n x i8] -> i8*
    llvm::Value *FormatStrPtr =
        Builder.CreatePointerCast(PrintfFormatStrVar, PrintfArgTy, "formatStr");

    
    //inject a call to printf
    Builder.CreateCall(
        Printf, {FormatStrPtr, print_stmt, Builder.getInt32(F.arg_size())});
    
  }

  return;
}

void DebloatPass::logDecFunctions(llvm::Module &M){
  std::ofstream decFile("declaration_functions.log", std::ios_base::app);
  for (Function &F : M){
    if (F.isDeclaration()){
      //output to decleration log
      if (decFile.is_open()) {
        decFile << F.getName().str() << "\n";
      }
    }
  }
  decFile.close();
  return;
}

bool getReturnInstruction(Function *F, Type *retType) {
  //Creating a return instruction will keep LLVM from converting the empties function into a declaration
  LLVMContext& context = F->getContext();
  BasicBlock *BB = BasicBlock::Create(context, "", F); 
  if (retType->isVoidTy()){
    ReturnInst *ret = ReturnInst::Create(context, BB);
    return true;
  }
  if(retType->isIntegerTy()){
    ReturnInst *ret =  ReturnInst::Create(context, ConstantInt::get(retType, 0, false), BB);
    return true;
  }
  if(retType->isFloatTy()){
    ReturnInst *ret =  ReturnInst::Create(context, ConstantFP::get(retType, 0), BB);
    return true;
  }
  if(retType->isPointerTy()){
    PointerType *ptr_type = dyn_cast<PointerType>(retType);
    ReturnInst *ret =  ReturnInst::Create(context, ConstantPointerNull::get(ptr_type), BB);
    return true;
  }
  #ifdef DEBUG
  errs() << "Unidentifiable Return Type. Reutrning a void return inst\n";
  #endif
  ReturnInst *ret =  ReturnInst::Create(context, BB);
  return false;

}

void DebloatPass::destroyFunction(llvm::Function *F/*, Constant *PrintfFormatStrVar, PointerType *PrintfArgTy, FunctionCallee Printf*/){
  #ifdef DEBUG
  errs() << "\tDestroying\n";
  #endif
  // Removes all references to this function from other instructions
  F->dropAllReferences();
  // Make sure function cannot be accessed from outside this module
  F->setLinkage(GlobalValue::InternalLinkage);
  bool success = getReturnInstruction(F, F->getReturnType());
  #ifdef DEBUG
  if (success){
    //errs() << "succesfully added a ret instruction.\n";
  } else {
    errs() << "Failed to create a valid ret instrcution.\n";
  }
  #endif
  /*
  #ifdef PRINTFDEL
  IRBuilder<> Builder(&*F->getEntryBlock().getFirstInsertionPt());
  auto FuncName = Builder.CreateGlobalStringPtr(F->getName());
  llvm::Value *FormatStrPtr =
        Builder.CreatePointerCast(PrintfFormatStrVar, PrintfArgTy, "formatStr");
  Builder.CreateCall(
        Printf, {FormatStrPtr, FuncName, Builder.getInt32(F->arg_size())});
  #endif
  */
}

void DebloatPass::logDeletedFunctions(std::set<std::string> funcs_to_delete){
  std::ofstream outFile("deleted_functions.log", std::ios_base::app);
  for (const std::string& func : funcs_to_delete) {
    if (outFile.is_open()) {
      outFile << func << "\n";
    }
  }
  outFile.close();
  return;
}

void logTracedFunctions(std::set<llvm::Function *> funcs){
  std::ofstream outFile("kept_functions.log", std::ios_base::app);
  for (auto F : funcs) {
    if (outFile.is_open()) {
      outFile << F->getName().str() << "\n";
    }
  }
  outFile.close();
  return;
}

bool DebloatPass::removeNonTracedFuncs(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  bool modified = false;
  /*
  #ifdef PRINTFDEL
  // Init printf
  auto &CTX = M.getContext();
  PointerType *PrintfArgTy = PointerType::getUnqual(Type::getInt8Ty(CTX));

  // STEP 1: Inject the declaration of printf
  // ----------------------------------------
  // Create (or _get_ in cases where it's already available) the following
  // declaration in the IR module:
  //    declare i32 @printf(i8*, ...)
  // It corresponds to the following C declaration:
  //    int printf(char *, ...)
  FunctionType *PrintfTy = FunctionType::get(
      IntegerType::getInt32Ty(CTX),
      PrintfArgTy,
      true);

  FunctionCallee Printf = M.getOrInsertFunction("printf", PrintfTy);

  // Set attributes as per inferLibFuncAttributes in BuildLibCalls.cpp
  Function *PrintfF = dyn_cast<Function>(Printf.getCallee());
  PrintfF->setDoesNotThrow();
  PrintfF->addParamAttr(0, Attribute::NoCapture);
  PrintfF->addParamAttr(0, Attribute::ReadOnly);


  // STEP 2: Inject a global variable that will hold the printf format string
  // ------------------------------------------------------------------------
  llvm::Constant *PrintfFormatStr = llvm::ConstantDataArray::getString(
      CTX, "Calling a deleted function:%s\n");

  Constant *PrintfFormatStrVar =
      M.getOrInsertGlobal("PrintfFormatStr", PrintfFormatStr->getType());
  dyn_cast<GlobalVariable>(PrintfFormatStrVar)->setInitializer(PrintfFormatStr);
  #endif
  */

  std::set<std::string> funcs_to_delete;
  // Iterate over functions in the module

 

  for (Function &F : M){
    if (F.isDeclaration())
      continue;

    // Check if the function name is in the traced_func_names vector
    if (std::find(missed_runtime_func_names.begin(), missed_runtime_func_names.end(), F.getName()) != missed_runtime_func_names.end()) {
      // TO DO: Remove this when find a way to autmatically do this
      #ifdef DEBUG
      errs() << "Runtime: " << F.getName().str() << "\n";
      #endif
      missed_runtime_funcs.insert(&F);
      continue;
    } 
    else if (std::find(traced_func_names.begin(), traced_func_names.end(), F.getName()) != traced_func_names.end()) {
      // Match found
      #ifdef DEBUG
      errs() << "Original trace: " << F.getName().str() << "\n";
      #endif
      traced_funcs.insert(&F);
      continue;
    } 
    else if (std::find(static_module_func_names.begin(), static_module_func_names.end(), F.getName()) != static_module_func_names.end()) {
      // Match found
      #ifdef DEBUG
      errs() << "Static Module: " << F.getName().str() << "\n";
      #endif
      static_module_funcs.insert(&F);
      continue;
    } 
    else if (F.getName().str().find("error") != std::string::npos){
      //keep error related functions
      traced_funcs.insert(&F);
      continue;
    }
    else if (F.getName().str().find("log") != std::string::npos){
      //keep logging related functions
      traced_funcs.insert(&F);
      continue;
    }
    //else if (F.getName().str().find("http") != std::string::npos){
      //keep logging related functions
      //traced_funcs.insert(&F);
      //continue;
    //}
    else{
      funcs_to_delete.insert(F.getName().str());
      continue;
    }
	}

  #ifdef DEBUG
  // Display deleted function names
  /*errs() << "Functions of traced_funcs:\n";
  for (auto Func : funcs_to_delete) {
      errs() << Func->getName().str() << "\n";
  }*/
  errs() << "Num functions to erase: " << funcs_to_delete.size() << "\n";
  errs() << "Num runtime funcs: " << missed_runtime_funcs.size() << "\n";
  errs() << "Num traced funcs: " << traced_funcs.size() << "\n";
  errs() << "Num static module funcs: " << static_module_funcs.size() << "\n";
  logTracedFunctions(traced_funcs);
  logTracedFunctions(missed_runtime_funcs);
  #endif

  //getCallsTo_DefUse(funcs_to_delete, M);
  
  int i = 0;
  errs() << "funcs_to_delete:\n";
  for (auto func_name : funcs_to_delete) {
    errs() << func_name << "\n";
    Function *F = M.getFunction(func_name);
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
    //destroyFunction(F, PrintfFormatStrVar, PrintfArgTy, Printf);
    destroyFunction(F);

    //slowCallDeletion(F, M);
    //deleteCallsTo_DefUse(F->getName().str());
    //deleteCallsTo(F->getName().str());
    //removes all uses of the function and the function itself
    /*
    for (User* U : F->users()) {
      CallBase   *CB = dyn_cast<CallBase>(U);
      CallInst   *CI = dyn_cast<CallInst>(U);
      InvokeInst *II = dyn_cast<InvokeInst>(U);
      if(CB){
        if (CI) {
          #ifdef DEBUG
          //errs() << "Erasing use" << *CI << "...\n";
          errs() << "Erasing use...\n";
          #endif
          //CI->eraseFromParent(); // Remove the call instruction
          CI->deleteValue();
          CI = nullptr;
        }
        if (II){
          #ifdef DEBUG
          //errs() << "Erasing use" << *II << "...\n";
          errs() << "Erasing use...\n";
          #endif
          //II->eraseFromParent(); // Remove the call instruction
          
          II->deleteValue();
          II = nullptr;
        }
      }
    }
    F->clearMetadata();
    F->eraseFromParent();
    */
    
    
    #ifdef DEBUG
    //errs() << "Erased\n";
    #endif
    i++;
    modified = true;
  }
  
  #ifdef DEBUG
  errs() << "Running DCE & Strip passes\n";
  #endif
  GlobalDCEPass().run(M, MAM);
  StripDeadPrototypesPass().run(M, MAM);
  #ifdef DEBUG
  logDeletedFunctions(funcs_to_delete);
  #endif
  return modified;
}

bool DebloatPass::initStaticModuleFuncNames(){
  std::string file_path = "/home/user/passes/py_scripts/static_funcs.txt";

  // Open the file
  std::ifstream file(file_path);

  // Check if the file is opened successfully
  if (!file.is_open()) {
      errs() << "Error opening file: " << file_path << "\n";
      return false;
  }

  // Read the file line by line
  std::string line;
  while (std::getline(file, line)) {
      // Add each line (function name) to the vector
      static_module_func_names.push_back(line);
  }

  // Close the file
  file.close();

  #ifdef DEBUG
  /*
  errs() << "Function Names of missed_runtime_func_names:\n";
  for (const auto& name : missed_runtime_func_names) {
      errs() << name << "\n";
  }*/
  #endif
  return true;
}

bool DebloatPass::initMissedRuntimeFuncNames() {
  std::string file_path = "/home/user/passes/unique_missed_runtime_funcs.log";

  // Open the file
  std::ifstream file(file_path);

  // Check if the file is opened successfully
  if (!file.is_open()) {
      errs() << "Error opening file: " << file_path << "\n";
      return false;
  }

  // Read the file line by line
  std::string line;
  while (std::getline(file, line)) {
      // Add each line (function name) to the vector
      missed_runtime_func_names.push_back(line);
  }

  // Close the file
  file.close();

  #ifdef DEBUG
  /*
  errs() << "Function Names of missed_runtime_func_names:\n";
  for (const auto& name : missed_runtime_func_names) {
      errs() << name << "\n";
  }*/
  #endif
  return true;
}

bool DebloatPass::initTracedFuncNames() {
  std::string file_path = "/home/user/passes/py_scripts/orig_nginx_pin.log";

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



/*********************    UNUSED FUNCTIONS -- DIDNT WORK    *********************/

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
                std::string name = cf->getName().str();
                #ifdef DEBUG
                errs() << "Found call to function I need to delete\n";
                errs() << "\t" << name << "\n";
                #endif
                del_insts[name].push_back(dyn_cast<Instruction>(&I));
              }

            }
      }
    }
  }
}

void DebloatPass::deleteCallsTo(std::string name){
  auto it = del_insts.find(name);
  if (it != del_insts.end()) {
    for (Instruction* CB : it->second){
      #ifdef DEBUG
      errs() << "Replacing Instruction: " << *CB << "\n";
      #endif
      // Create an UndefValue with the same type as the result of the call
      Value *Undef = UndefValue::get(CB->getType());

      // Replace the CallInst with Undef
      CB->replaceAllUsesWith(Undef);
      #ifdef DEBUG
      errs() << "\t with: " << *CB << "\n";
      #endif

      // Erase the CallInst from its parent basic block
      CB->eraseFromParent();
      #ifdef DEBUG
      errs() << "\tInstruction erased.\n";
      #endif

    }
  } else {
    #ifdef DEBUG
    errs() << "No instructions in map\n";
    #endif
  }
  return;
}

void DebloatPass::slowCallDeletion(llvm::Function *del_func, llvm::Module &M){
for (Function &F : M){
    for (auto &B : F){
      for (auto &I : B){
        CallBase   *CB = dyn_cast<CallBase>(&I);
        CallInst   *CI = dyn_cast<CallInst>(&I);
        InvokeInst *II = dyn_cast<InvokeInst>(&I);
        if(CB){
          Function *cf = CB->getCalledFunction();
          if (cf == del_func){
            std::string name = cf->getName().str();
            #ifdef DEBUG
            errs() << "Found call to " << name << "...deleting\n";
            #endif
            CB->removeFromParent();
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

void findUsesOfFunction(Function *F) {
  for (User *U : F->users()) {
    if (Instruction *I = dyn_cast<Instruction>(U)) {
      // I is an instruction that uses the function F
      #ifdef DEBUG
      errs() << "Found use: " << *I << "\n";
      #endif
      
    }
  }
}

void DebloatPass::getCallsTo_DefUse(std::set<std::string> funcs_to_delete, Module &M){
  auto &CTX = M.getContext();
  for (auto func_name : funcs_to_delete) {
    Function *F = M.getFunction(func_name);
    for (User *U : F->users()) {
      if (Instruction *I = dyn_cast<Instruction>(U)) {
        //instruction is in a function i wil delete anyways. 
        //trying to delete after the function has been deleted will cause errors
        if (funcs_to_delete.count(I->getFunction()->getName().str())){
          #ifdef DEBUG
          //errs() << "Instruction exists in a function marked for deletion. skipping.\n";
          #endif
          continue;
        }

        // I is an instruction that uses the function F
        #ifdef DEBUG
        //errs() << "Found use: " << *I << "\n";
        #endif
        /*
        FunctionType *PlaceholderFuncType = FunctionType::get(Type::getVoidTy(CTX), false);
        Function *PlaceholderFunc = Function::Create(PlaceholderFuncType, GlobalValue::ExternalLinkage, "placeholder_func", &M);

        
        
        CallInst *CI = dyn_cast<CallInst>(I);
        InvokeInst *II = dyn_cast<InvokeInst>(I);
        if (CI) {
            CI->setCalledFunction(PlaceholderFunc);
            #ifdef DEBUG
            errs() << "New inst: " << *CI << "\n";
            #endif
        } else if (II) {
            II->setCalledFunction(PlaceholderFunc);
            #ifdef DEBUG
            errs() << "New inst: " << *II << "\n";
            #endif
        }
        */
        del_insts[F->getName().str()].push_back(I);
      }
    }
  }

  //iterate and chang all isntrcutions
  /*
  for (const auto &entry : del_insts) {
    for (Instruction *inst : entry.second) {
      Instruction *NopInst = BinaryOperator::Create(Instruction::BinaryOps::Add, ConstantInt::get(Type::getInt32Ty(CTX), 0), ConstantInt::get(Type::getInt32Ty(CTX), 0), "nop", inst);
      ReplaceInstWithInst(inst, NopInst);
      #ifdef DEBUG
      errs() << "New inst: " << *inst << "\n";
      errs() << "\treplacement: " << *NopInst << "\n";
      #endif
    }
  }*/
  
}

void DebloatPass::deleteCallsTo_DefUse(std::string name){
  auto it = del_insts.find(name);
  if (it != del_insts.end()) {
    while (!it->second.empty()) {
      Instruction* inst = it->second.back();
      it->second.pop_back();
      // Create an UndefValue with the same type as the result of the call
      //Value *Undef = UndefValue::get(inst->getType());

      // Replace the CallInst with Undef
      //inst->replaceAllUsesWith(Undef);
      #ifdef DEBUG
      //errs() << "\t First replaced with Undef Value: " << *inst << "\n";
      #endif
      if (inst){
        #ifdef DEBUG
        errs() << "Erasing Instruction: " << *inst << "\n";
        #endif
        // Erase the CallInst from its parent basic block
        inst->eraseFromParent();
        #ifdef DEBUG
        errs() << "\tInstruction erased.\n";
        #endif
      } else {
        #ifdef DEBUG
        errs() << "\tInstruction no longer referenced. Skipping deletion\n";
        #endif
        continue;
      }

    }
  } else {
    #ifdef DEBUG
    errs() << "No instructions in map\n";
    #endif
  }
  return;
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
