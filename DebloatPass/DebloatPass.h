#ifndef DEBLOAT_PASS_H
#define DEBLOAT_PASS_H

#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include <vector>
#include <map>
#include <set>
#include <string>
#include <iostream>
#include <fstream>

class DebloatPass : public llvm::PassInfoMixin<DebloatPass> {
public:
  llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  

  std::vector<std::string> traced_func_names;
  std::set<llvm::Function *> traced_funcs;
  std::vector<std::string> missed_runtime_func_names;
  std::set<llvm::Function *> missed_runtime_funcs;
  std::vector<std::string> static_module_func_names;
  std::set<llvm::Function *> static_module_funcs;
  

  std::map<std::string, std::vector<llvm::Instruction *>> del_insts;

  bool initTracedFuncNames();
  bool initMissedRuntimeFuncNames();
  bool initStaticModuleFuncNames();
  bool removeNonTracedFuncs(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  void getCallsTo(std::set<llvm::Function *> funcs_to_delete, llvm::Module &M);
  void deleteCallsTo(std::string name);
  void getCallsTo_DefUse(std::set<std::string> funcs_to_delete, llvm::Module &M);
  void deleteCallsTo_DefUse(std::string name);
  void slowCallDeletion(llvm::Function *F,llvm::Module &M);
  //void destroyFunction(llvm::Function *F, llvm::Constant *PrintfFormatStrVar, llvm::PointerType *PrintfArgTy, llvm::FunctionCallee Printf);
  void destroyFunction(llvm::Function *F);
  void printfAllFuncs(llvm::Module &M);

  void logDecFunctions(llvm::Module &M);
  void logDeletedFunctions(std::set<std::string> funcs_to_delete);

  bool runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  static bool isRequired() { return true; }
};

#endif //DEBLOAT_PASS_H
