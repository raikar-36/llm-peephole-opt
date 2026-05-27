define dso_local i32 @f_b021(i32 noundef %0) local_unnamed_addr #0 {
  %2 = add nsw i32 %0, -1
  %3 = and i32 %2, %0
  ret i32 %3
}
