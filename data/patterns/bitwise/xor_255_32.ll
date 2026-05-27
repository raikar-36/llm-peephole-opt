define i32 @pattern_xor_255_32(i32 %x) {
entry:
  %result = xor i32 %x, 255
  ret i32 %result
}
