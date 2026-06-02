define i32 @pattern_shifts_76(i32 %x, i32 %y) {
entry:
  %0 = shl i32 %x, 11
  %1 = shl i32 %y, 11
  %2 = add i32 %0, %1
  ret i32 %2
}