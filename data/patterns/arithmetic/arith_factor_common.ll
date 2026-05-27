define dso_local noundef i32 @f_a024(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = add i32 %1, 3
  %4 = mul i32 %3, %0
  ret i32 %4
}
