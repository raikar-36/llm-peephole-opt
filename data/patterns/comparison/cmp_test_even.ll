define dso_local noundef i32 @f_c005(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, 1
  %3 = xor i32 %2, 1
  ret i32 %3
}
