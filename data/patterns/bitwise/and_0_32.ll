define i32 @pattern_and_0_32(i32 %x) {
entry:
  %result = and i32 %x, 0
  ret i32 %result
}
