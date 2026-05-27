define dso_local noundef i32 @f_shl8(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, 16777215
  ret i32 %2
}
