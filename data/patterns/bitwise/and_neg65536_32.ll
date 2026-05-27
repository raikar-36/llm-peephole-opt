define i32 @pattern_and_neg65536_32(i32 %x) {
entry:
  %result = and i32 %x, -65536
  ret i32 %result
}
