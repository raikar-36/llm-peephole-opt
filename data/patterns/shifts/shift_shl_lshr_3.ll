define dso_local noundef i32 @f_shl3(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, 536870911
  ret i32 %2
}
