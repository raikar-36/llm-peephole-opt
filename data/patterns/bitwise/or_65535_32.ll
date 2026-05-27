define i32 @pattern_or_65535_32(i32 %x) {
entry:
  %result = or i32 %x, 65535
  ret i32 %result
}
