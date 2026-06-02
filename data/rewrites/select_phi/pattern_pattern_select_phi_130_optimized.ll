define i32 @pattern_select_phi_130(i1 %cond, i32 %x, i32 %y) {
entry:
  %1 = select i1 %cond, i32 %x, i32 %y
  %2 = add i32 %1, 5
  ret i32 %2
}