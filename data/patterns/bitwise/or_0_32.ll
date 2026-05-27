define i32 @pattern_or_0_32(i32 %x) {
entry:
  %result = or i32 %x, 0
  ret i32 %result
}
