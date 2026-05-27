define i32 @chain_sub_add_4_4(i32 %x) {
entry:
  %tmp = sub i32 %x, 4
  %result = add i32 %tmp, 4
  ret i32 %result
}
