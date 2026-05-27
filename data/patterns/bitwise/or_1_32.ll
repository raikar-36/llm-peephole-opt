define i32 @pattern_or_1_32(i32 %x) {
entry:
  %result = or i32 %x, 1
  ret i32 %result
}
