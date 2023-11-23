#ifndef DEBLOAT_PASS_H
#define DEBLOAT_PASS_H

#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

#include <vector>
#include <set>
#include <string>
#include <iostream>
#include <fstream>

class DebloatPass : public llvm::PassInfoMixin<DebloatPass> {
public:
  llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  

  std::vector<std::string> traced_func_names;
  std::set<llvm::Function *> traced_funcs;
  std::set<llvm::Instruction *> del_insts;

  bool initTracedFuncNames();
  bool removeNonTracedFuncsNgx(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  void getCallsTo(std::set<llvm::Function *> funcs_to_delete, llvm::Module &M);

  bool runOnModule(llvm::Module &M, llvm::ModuleAnalysisManager &MAM);
  static bool isRequired() { return true; }
};

#endif //DEBLOAT_PASS_H
