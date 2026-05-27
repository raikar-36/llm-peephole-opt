define i32 @pattern_mul_65535_32(i32 %x) {
entry:
  %result = mul i32 %x, 65535
  ret i32 %result
}
