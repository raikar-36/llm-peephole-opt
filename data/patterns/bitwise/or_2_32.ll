define i32 @pattern_or_2_32(i32 %x) {
entry:
  %result = or i32 %x, 2
  ret i32 %result
}
