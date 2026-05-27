define dso_local i32 @f_x008(i32 noundef %0, i32 noundef %1, i32 noundef %2) local_unnamed_addr #0 {
  %4 = add nsw i32 %1, %0
  %5 = add nsw i32 %4, %2
  ret i32 %5
}
