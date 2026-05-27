define i32 @pattern_and_neg128_32(i32 %x) {
entry:
  %result = and i32 %x, -128
  ret i32 %result
}
