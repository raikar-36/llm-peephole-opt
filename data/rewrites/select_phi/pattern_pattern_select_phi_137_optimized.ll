define i32 @pattern_select_phi_137(i1 %cond, i32 %x, i32 %y) {
entry:
  %1 = select i1 %cond, i32 %x, i32 %y
  %2 = add i32 %1, 12
  ret i32 %2
}