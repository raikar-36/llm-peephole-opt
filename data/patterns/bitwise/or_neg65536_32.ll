define i32 @pattern_or_neg65536_32(i32 %x) {
entry:
  %result = or i32 %x, -65536
  ret i32 %result
}
