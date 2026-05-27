define i64 @pattern_mul_255_64(i64 %x) {
entry:
  %result = mul i64 %x, 255
  ret i64 %result
}
