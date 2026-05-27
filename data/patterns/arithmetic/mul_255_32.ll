define i32 @pattern_mul_255_32(i32 %x) {
entry:
  %result = mul i32 %x, 255
  ret i32 %result
}
