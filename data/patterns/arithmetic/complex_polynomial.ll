define dso_local i32 @f_x007(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add i32 %0, 2
  %3 = mul i32 %2, %0
  %4 = add nsw i32 %3, 1
  ret i32 %4
}
