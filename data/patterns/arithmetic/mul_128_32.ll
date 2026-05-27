define i32 @pattern_mul_128_32(i32 %x) {
entry:
  %result = mul i32 %x, 128
  ret i32 %result
}
