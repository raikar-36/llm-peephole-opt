define i32 @pattern_shifts_90(i32 %x, i32 %y) {
entry:
  %0 = shl i32 %x, 25
  %1 = shl i32 %y, 25
  %2 = add i32 %0, %1
  ret i32 %2
}