#ifndef DEBLOAT_PASS_H
#define DEBLOAT_PASS_H

#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include <vector>
#include <map>
#include <set>
#include <string>

class DebloatPass : public llvm::PassInfoMixin<DebloatPass> {
public:
  llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  

  std::set<std::string> traced_func_names;
  std::set<llvm::Function *> traced_funcs;
  std::set<std::string> static_module_func_names;
  std::set<llvm::Function *> static_module_funcs;
  std::set<std::string> cyclo_func_names;
  std::set<llvm::Function *> cyclo_funcs;
  std::map<std::string, int> cyclo_complexity;
  std::set<std::string> scc_func_names;
  std::set<llvm::Function *> scc_funcs;
  

  std::map<std::string, std::vector<llvm::Instruction *>> del_insts;

  bool initTracedFuncNames(bool nginx);
  bool initStaticModuleFuncNames(bool nginx);
  bool removeNonTracedFuncs(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  bool calculateFuncCycloComplexity(llvm::Module &M);
  void calculateCycloStats();
  void findSCCs(llvm::Module &M);
  void getControlDeps(llvm::Module &M);

  //void destroyFunction(llvm::Function *F, llvm::Constant *PrintfFormatStrVar, llvm::PointerType *PrintfArgTy, llvm::FunctionCallee Printf);
  void destroyFunction(llvm::Function *F);
  void printfAllFuncs(llvm::Module &M);

  void logDecFunctions(llvm::Module &M);
  void logDeletedFunctions(std::set<std::string> funcs_to_delete);

  bool runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  static bool isRequired() { return true; }
};

#endif //DEBLOAT_PASS_H
