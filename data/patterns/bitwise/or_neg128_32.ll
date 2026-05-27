define i32 @pattern_or_neg128_32(i32 %x) {
entry:
  %result = or i32 %x, -128
  ret i32 %result
}
