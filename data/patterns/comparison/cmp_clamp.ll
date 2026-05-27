define dso_local noundef i32 @f_c012(i32 noundef %0) local_unnamed_addr #0 {
  %2 = tail call i32 @llvm.smin.i32(i32 %0, i32 255)
  %3 = tail call i32 @llvm.smax.i32(i32 %2, i32 0)
  ret i32 %3
}
