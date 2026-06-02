define i32 @pattern_select_phi_138(i1 %cond, i32 %x, i32 %y) {
entry:
  %0 = select i1 %cond, i32 %x, i32 %y
  %1 = add i32 %0, 13
  ret i32 %1
}