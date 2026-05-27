define dso_local i32 @f_b023(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = shl nsw i32 -1, %1
  %4 = xor i32 %3, -1
  %5 = and i32 %4, %0
  ret i32 %5
}
