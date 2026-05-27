define dso_local noundef i32 @f_bm_ffff_ff(i32 noundef %0) local_unnamed_addr #0 {
  %2 = and i32 %0, 255
  ret i32 %2
}
