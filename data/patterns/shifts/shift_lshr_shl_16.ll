define dso_local noundef i32 @f_lshr16(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, -65536
  ret i32 %2
}
