define i32 @pattern_ashr_16_32(i32 %x) {
entry:
  %result = ashr i32 %x, 16
  ret i32 %result
}
