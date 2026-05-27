define i32 @pattern_xor_65535_32(i32 %x) {
entry:
  %result = xor i32 %x, 65535
  ret i32 %result
}
