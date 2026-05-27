define dso_local noundef i32 @f_o008(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = tail call i32 @llvm.usub.sat.i32(i32 %0, i32 %1)
  ret i32 %3
}
