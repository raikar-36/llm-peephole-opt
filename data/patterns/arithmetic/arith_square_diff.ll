define dso_local i32 @f_a025(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = add nsw i32 %1, %0
  %4 = sub nsw i32 %0, %1
  %5 = mul nsw i32 %3, %4
  ret i32 %5
}
