define i32 @pattern_shifts_85(i32 %x, i32 %y) {
entry:
  %1 = add i32 %x, %y
  %2 = shl i32 %1, 20
  ret i32 %2
}