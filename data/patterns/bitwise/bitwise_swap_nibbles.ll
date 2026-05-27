define dso_local noundef zeroext i8 @f_b024(i8 noundef zeroext %0) local_unnamed_addr #0 {
  %2 = tail call i8 @llvm.fshl.i8(i8 %0, i8 %0, i8 4)
  ret i8 %2
}
