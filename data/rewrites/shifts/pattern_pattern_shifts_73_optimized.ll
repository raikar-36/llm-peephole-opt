define i32 @pattern_shifts_73(i32 %x, i32 %y) {
entry:
  %1 = add i32 %x, %y
  %2 = shl i32 %1, 8
  ret i32 %2
}