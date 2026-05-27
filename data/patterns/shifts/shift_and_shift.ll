define dso_local noundef i32 @f_s015(i32 noundef %0) local_unnamed_addr #0 {
  %2 = shl i32 %0, 8
  %3 = and i32 %2, 65280
  ret i32 %3
}
