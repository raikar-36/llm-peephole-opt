define i32 @pattern_select_phi_140(i1 %cond, i32 %x, i32 %y) {
entry:
  %0 = add i32 %x, 15
  %1 = add i32 %y, 15
  %2 = select i1 %cond, i32 %0, i32 %1
  ret i32 %2
}