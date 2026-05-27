define dso_local i32 @f_t010(i32 noundef %0) local_unnamed_addr #0 {
  %2 = uitofp i32 %0 to float
  %3 = fptoui float %2 to i32
  ret i32 %3
}
