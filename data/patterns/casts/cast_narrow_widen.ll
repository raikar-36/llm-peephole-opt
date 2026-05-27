define dso_local i64 @f_t009(i64 noundef %0) local_unnamed_addr #0 {
  %2 = shl i64 %0, 32
  %3 = ashr exact i64 %2, 32
  ret i64 %3
}
