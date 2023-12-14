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
#include "llvm/IR/Instructions.h"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/Timer.h"

#include "llvm/Analysis/CallGraph.h"
#include "llvm/IR/Function.h"
#include "llvm/Pass.h"
#include "llvm/Support/GraphWriter.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/LoopPass.h"
#include "llvm/ADT/SCCIterator.h"

#include <algorithm>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include <algorithm>
#include <cmath>

using namespace llvm;

static cl::opt<bool> mydebug("my-debug", cl::desc("Enable errs() print statements"), cl::init(false));
#define MYDEBUG mydebug

//static cl::opt<bool> printfall("printf-all", cl::desc("Enable printf statements for all functions"), cl::init(false));
//#define PRINTFALL printfall

PreservedAnalyses DebloatPass::run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  #ifdef MYDEBUG
  //errs() << "Verbose debug messages enabled.\n";
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
      #ifdef MYDEBUG
      errs() << "declaration_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef MYDEBUG
      //errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
  try {
      fs::remove(filename2);
      #ifdef MYDEBUG
      //errs() << "kept_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef MYDEBUG
      //errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
  try {
      fs::remove(filename3);
      #ifdef MYDEBUG
      //errs() << "deleted_functions.log successfully deleted\n";
      #endif
  } catch (const std::filesystem::filesystem_error& e) {
      #ifdef MYDEBUG
      //errs() << "Error deleting file: " << e.what() << "\n";
      #endif
  }
}

void compareSets(std::set<std::string> set1, std::set<std::string> set2){
  // Create a set to store the common functions
  std::set<std::string> common;

  // Use std::set_intersection to find common elements
  std::set_intersection(set1.begin(), set1.end(), set2.begin(), set2.end(),
                        std::inserter(common, common.begin()));

  // Output the common functions
  //errs() << "Common functions: ";
  //for (const auto& functionName : common) {
  //    errs() << functionName << " ";
  //}
  //errs() << "\n";

  // Output the number of common functions
  errs() << "Set1: " << set1.size() << "\n";
  errs() << "Set2: " << set1.size() << "\n";
  errs() << "Number of common functions: " << common.size() << "\n";
}

bool DebloatPass::runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM){
  bool nginx = true;
  bool thttpd = false;
  Timer TimerObj1("PassTimer", "Timer for Complete Pass");
  Timer TimerObj2("CycloTimer", "Timer for Cyclo function");
  TimerObj1.startTimer();
  clearLogs();
  initTracedFuncNames(nginx);
  initStaticModuleFuncNames(nginx);
  //initTracedFuncNames(thttpd);
  //initStaticModuleFuncNames(thttpd);
  
  //TO DO: RE-add after gadget experiment
  //TimerObj2.startTimer();
  //calculateFuncCycloComplexity(M);
  //TimerObj2.stopTimer();
  //calculateCycloStats();

  //--//getControlDeps(M);
  //--//findSCCs(M);
  //--//compareSets(traced_func_names, scc_func_names);


  removeNonTracedFuncs(M, MAM);
  #ifdef MYDEBUG
  //errs() << "Finished removal. Checking module\n";
  #endif
  if (!verifyModule(M, &errs())) {
    errs() << "Module is well-formed.\n";
  } else {
      errs() << "Module has errors!\n";
  }
  #ifdef MYDEBUG
  logDecFunctions(M);
  //printfAllFuncs(M);
  #endif
  //printfAllFuncs(M);
  TimerObj1.stopTimer();
  double ElapsedTime1 = TimerObj1.getTotalTime().getWallTime();
  double ElapsedTime2 = TimerObj2.getTotalTime().getWallTime();

  errs() << "Pass Timer: " << ElapsedTime1 << "\n";
  errs() << "Cyclo Timer: " << ElapsedTime2 << "\n";

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
      CTX, "%s\n");

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
    auto it3 = static_module_funcs.find(&F);
    if (it != traced_funcs.end()) {
        // F is in traced_funcs
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
  #ifdef MYDEBUG
  //errs() << "Unidentifiable Return Type. Reutrning a void return inst\n";
  #endif
  ReturnInst *ret =  ReturnInst::Create(context, BB);
  return false;

}

void DebloatPass::destroyFunction(llvm::Function *F/*, Constant *PrintfFormatStrVar, PointerType *PrintfArgTy, FunctionCallee Printf*/){
  #ifdef MYDEBUG
  //errs() << "\tDestroying\n";
  #endif
  // Removes all references to this function from other instructions
  F->dropAllReferences();
  // Make sure function cannot be accessed from outside this module
  F->setLinkage(GlobalValue::InternalLinkage);
  bool success = getReturnInstruction(F, F->getReturnType());
  #ifdef MYDEBUG
  if (success){
    //errs() << "succesfully added a ret instruction.\n";
  } else {
    errs() << "Failed to create a valid ret instrcution.\n";
  }
  #endif
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
 
  std::set<std::string> funcs_to_delete;
  // Iterate over functions in the module

 

  for (Function &F : M){
    if (F.isDeclaration())
      continue;

    if (std::find(traced_func_names.begin(), traced_func_names.end(), F.getName()) != traced_func_names.end()) {
      // Match found
      #ifdef MYDEBUG
      //errs() << "Original trace: " << F.getName().str() << "\n";
      #endif
      traced_funcs.insert(&F);
      continue;
    } 
    else if (std::find(static_module_func_names.begin(), static_module_func_names.end(), F.getName()) != static_module_func_names.end()) {
      // Match found
      #ifdef MYDEBUG
      //errs() << "Static Module: " << F.getName().str() << "\n";
      #endif
      static_module_funcs.insert(&F);
      continue;
    } 
    else if (std::find(cyclo_func_names.begin(), cyclo_func_names.end(), F.getName()) != cyclo_func_names.end()) {
      // Match found
      #ifdef MYDEBUG
      //errs() << "Cyclo Complexity: " << F.getName().str() << "\n";
      #endif
      cyclo_funcs.insert(&F);
      continue;
    } 
    else if (F.getName().str().find("error") != std::string::npos){
      //keep error related functions
      // TO DO: Add back after gadget experiment
      //traced_funcs.insert(&F);
      continue;
    }
    else if (F.getName().str().find("log") != std::string::npos){
      //keep logging related functions
      // TO DO: Add back after gadget experiment
      //traced_funcs.insert(&F);
      continue;
    }
    else{
      funcs_to_delete.insert(F.getName().str());
      continue;
    }
	}

  #ifdef MYDEBUG 
  // Display deleted function names
  /*errs() << "Functions of traced_funcs:\n";
  for (auto Func : funcs_to_delete) {
      errs() << Func->getName().str() << "\n";
  }*/
  errs() << "Num functions to erase: " << funcs_to_delete.size() << "\n";
  errs() << "Num traced funcs: " << traced_funcs.size() << "\n";
  errs() << "Num static module funcs: " << static_module_funcs.size() << "\n";
  logTracedFunctions(traced_funcs);
  #endif

  //getCallsTo_DefUse(funcs_to_delete, M);
  
  int i = 0;
  //errs() << "funcs_to_delete:\n";
  for (auto func_name : funcs_to_delete) {
    //errs() << func_name << "\n";
    Function *F = M.getFunction(func_name);
    #ifdef MYDEBUG
    if (i%100 == 0){
      //errs() << "Erased " << i << " functions.\n";
    }
    #endif
    if (!F){
      #ifdef MYDEBUG
      //errs() << "F is null. Cannot delete\n";
      #endif
      continue;
    }
    if (F->getName().empty()) {
      #ifdef MYDEBUG
      //errs() << "No named function. Cannot delete\n";
      #endif
      continue;
    }
    #ifdef MYDEBUG
    //errs() << "Erasing --" << F->getName().str() << "--\n";
    #endif
    destroyFunction(F);
    
    
    #ifdef MYDEBUG
    //errs() << "Erased\n";
    #endif
    i++;
    modified = true;
  }
  
  #ifdef MYDEBUG
  //errs() << "Running DCE & Strip passes\n";
  #endif
  GlobalDCEPass().run(M, MAM);
  StripDeadPrototypesPass().run(M, MAM);
  #ifdef MYDEBUG
  logDeletedFunctions(funcs_to_delete);
  #endif
  return modified;
}

bool DebloatPass::initStaticModuleFuncNames(bool nginx){
  std::string dir = "/home/user/passes/pass_files/";
  if (nginx) {
    dir += "nginx/";
  } else {
    dir += "thttpd/";
  }

  std::string file_path = dir + "static_funcs_all_tests.txt";
  // Open the file
  std::ifstream file(file_path);

  // Check if the file is opened successfully
  if (!file.is_open()) {
      //errs() << "Error opening file: " << file_path << "\n";
      return false;
  }

  // Read the file line by line
  std::string line;
  while (std::getline(file, line)) {
      // Add each line (function name) to the vector
      static_module_func_names.insert(line);
  }

  // Close the file
  file.close();

  #ifdef MYDEBUG

  #endif
  return true;
}

bool DebloatPass::initTracedFuncNames(bool nginx) {

  std::string dir = "/home/user/passes/pass_files/";
  if (nginx) {
    dir += "nginx/";
  } else {
    dir += "thttpd/";
  }
  //std::string file_path = "/home/user/passes/pass_files/orig_nginx_pin.log";
  //std::string file_path2 = "/home/user/passes/pass_files/orig_nginx_llvm.log";
  std::string file_path = dir + "orig_pin.log";
  std::string file_path2 = dir + "orig_llvm_all_tests.log";
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
      traced_func_names.insert(line);
  }

  // Close the file
  file.close();

  std::ifstream file2(file_path2);

  // Check if the file is opened successfully
  if (!file2.is_open()) {
      std::cerr << "Error opening file: " << file_path2 << std::endl;
      return false;
  }

  // Read the file line by line
  std::string line2;
  while (std::getline(file2, line2)) {
      // Add each line (function name) to the vector
      traced_func_names.insert(line2);
  }

  // Close the file
  file2.close();

  return true;
}

bool DebloatPass::calculateFuncCycloComplexity(llvm::Module &M){
  for (Function &F : M){
    if (F.isDeclaration())
      continue;
    int complexity = 1; // formula: M = D + 1 where D is decision points
    for (BasicBlock &BB : F) {
      Instruction *TI = BB.getTerminator();
      // Check if the terminator instruction is a branch with multiple successors or a switch instruction
      if (TI->getNumSuccessors() > 1 || isa<SwitchInst>(TI)) {
          complexity++;
      }
    }
    cyclo_complexity[F.getName().str()] = complexity;
    //errs() << "Complexity of " << F.getName().str() << ": " << complexity << "\n";
  }
  return false;
}

void DebloatPass::getControlDeps(llvm::Module &M){
  CallGraph CG = CallGraph(M);
  // Perform a reverse topological sort using the SCCIterator
  for (scc_iterator<CallGraph *> I = scc_begin(&CG); !I.isAtEnd(); ++I) {
    const std::vector<CallGraphNode *> &SCC = *I;
    
    // SCC represents a Strongly Connected Component (a set of functions that call each other)
    // Perform further analysis or actions based on SCC if needed
    // Functions within the same SCC do not have a well-defined order, but they have dependencies on each other
    errs() << "Functions in SCC:\n";
    for (CallGraphNode *CGN : SCC) {
      Function *F = CGN->getFunction();
      if (F && !F->isDeclaration()) {
        errs() << "\t" << F->getName().str() << "\n";
      }
    }
  }
  return;
}

void DebloatPass::calculateCycloStats(){
   std::vector<int> complexityValues;
    for (const auto &entry : cyclo_complexity) {
      //errs() << "Complexity Function: " << entry.first << ", Complexity Score: " << entry.second << "\n";
        complexityValues.push_back(entry.second);
    }
    // Calculate mean
    double mean = std::accumulate(complexityValues.begin(), complexityValues.end(), 0.0) / complexityValues.size();

    // Calculate median
    std::sort(complexityValues.begin(), complexityValues.end());
    double median;
    if (complexityValues.size() % 2 == 0) {
        median = (complexityValues[complexityValues.size() / 2 - 1] + complexityValues[complexityValues.size() / 2]) / 2.0;
    } else {
        median = complexityValues[complexityValues.size() / 2];
    }

    // Calculate standard deviation
    double sumSquaredDifferences = 0.0;
    for (const auto &value : complexityValues) {
        sumSquaredDifferences += std::pow(value - mean, 2);
    }
    double standardDeviation = std::sqrt(sumSquaredDifferences / complexityValues.size());
  // Identify functions with complexity values outside 1 standard deviation
    for (const auto &entry : cyclo_complexity) {
        if (std::abs(entry.second - mean) > standardDeviation) {
            cyclo_func_names.insert(entry.first);
            //errs() << "Cyclo-Complexity: Keep " << entry.first << "\n"; 
        }
    }
    
}

void DebloatPass::findSCCs(llvm::Module &M){
  CallGraph CG(M);
  for (scc_iterator<CallGraph *> I = scc_begin(&CG), E = scc_end(&CG); I != E; ++I) {
    const std::vector<CallGraphNode *> &SCCNodes = *I;
    // Check if any of the SCC nodes correspond to functions of interest
    bool containsFunctionOfInterest = false;
    for (CallGraphNode *Node : SCCNodes) {
      if (Function *F = Node->getFunction()) {
        // Check if the function is not in functionsOfInterest
        if (std::find(traced_func_names.begin(), traced_func_names.end(), F->getName()) == traced_func_names.end()) {
            // Add the function to the set
            scc_funcs.insert(F);
            scc_func_names.insert(F->getName().str());
            //errs() << "Adding " << F->getName().str() << " to SCC set.\n";
        }
      }
    }
   }
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
