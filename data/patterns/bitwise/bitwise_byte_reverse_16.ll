define dso_local noundef zeroext i16 @f_b025(i16 noundef zeroext %0) local_unnamed_addr #0 {
  %2 = tail call i16 @llvm.bswap.i16(i16 %0)
  ret i16 %2
}
