define i32 @pattern_shifts_87(i32 %x, i32 %y) {
entry:
  %1 = add i32 %x, %y
  %2 = shl i32 %1, 22
  ret i32 %2
}