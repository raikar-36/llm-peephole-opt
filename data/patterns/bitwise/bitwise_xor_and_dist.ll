define dso_local noundef i32 @f_b030(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = xor i32 %1, -1
  %4 = and i32 %3, %0
  ret i32 %4
}
