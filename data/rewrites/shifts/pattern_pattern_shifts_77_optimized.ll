define i32 @pattern_shifts_77(i32 %x, i32 %y) {
entry:
  %1 = add i32 %x, %y
  %2 = shl i32 %1, 12
  ret i32 %2
}