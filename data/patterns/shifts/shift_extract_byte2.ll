define dso_local noundef i32 @f_s012(i32 noundef %0) local_unnamed_addr #0 {
  %2 = lshr i32 %0, 16
  %3 = and i32 %2, 255
  ret i32 %3
}
