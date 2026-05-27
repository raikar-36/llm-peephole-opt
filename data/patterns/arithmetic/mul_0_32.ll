define i32 @pattern_mul_0_32(i32 %x) {
entry:
  %result = mul i32 %x, 0
  ret i32 %result
}
