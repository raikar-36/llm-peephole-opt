define i32 @pattern_shifts_74(i32 %x, i32 %y) {
entry:
  %0 = shl i32 %x, 9
  %1 = shl i32 %y, 9
  %2 = add i32 %0, %1
  ret i32 %2
}